package com.kun.card.integration;

import com.fasterxml.jackson.databind.JsonNode;
import com.kun.card.integration.KunOpenApiClient.PlatformException;
import com.kun.card.integration.KunOpenApiClient.TransportException;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

/**
 * 商务卡 · 预付虚拟卡 · Java 可落地流程。
 *
 * <pre>
 * 判态：平台 code + data.openCardStatus（SUCCESS / FAIL / PENDING）
 * 超时 / 5xx / 无法解析 → UNKNOWN → 仅用原 requestNo 查单，禁止再开
 * 明确 FAIL / 平台拒绝 → 修参后换新 requestNo
 * </pre>
 *
 * 依赖：Java 11+、Jackson databind。运行前配置环境变量（勿提交真实密钥）。
 */
public final class CommercialPrepaidFlow {

    public enum LocalOpenCardState {
        CREATED, ACCEPTING, PENDING, SUCCESS, FAIL, UNKNOWN
    }

    private final KunOpenApiClient client;
    private final String secretKey;
    private final String cardProductCode;

    public CommercialPrepaidFlow(KunOpenApiClient client, String secretKey, String cardProductCode) {
        this.client = client;
        this.secretKey = secretKey;
        this.cardProductCode = cardProductCode == null ? "" : cardProductCode;
    }

    public static String newRequestNo(String prefix) {
        return prefix + "_" + UUID.randomUUID().toString().replace("-", "").substring(0, 24);
    }

    public List<JsonNode> listCommercialVirtualProducts() throws Exception {
        Map<String, Object> body = new HashMap<>();
        body.put("requestNo", newRequestNo("bins"));
        body.put("secretKey", secretKey);
        body.put("ip", "127.0.0.1");
        JsonNode payload = client.postAndParse("/rest/v2.0/api/common/cardBins", body);
        JsonNode data = payload.get("data");
        List<JsonNode> out = new ArrayList<>();
        if (data == null || !data.isArray()) {
            return out;
        }
        for (JsonNode p : data) {
            if (!"COMMERCIAL".equals(text(p, "cardScene"))) {
                continue;
            }
            String types = text(p, "supportedCardTypes");
            if (types == null) {
                types = "V";
            }
            if (!types.toUpperCase(Locale.ROOT).contains("V")) {
                continue;
            }
            out.add(p);
        }
        return out;
    }

    public String addCardholder(String firstName, String lastName, String email) throws Exception {
        Map<String, Object> body = new HashMap<>();
        body.put("requestNo", newRequestNo("ch"));
        body.put("secretKey", secretKey);
        body.put("firstName", firstName);
        body.put("lastName", lastName);
        body.put("email", email.trim().toLowerCase(Locale.ROOT));
        JsonNode data = client.postAndParse(
                "/rest/v2.0/caas/customer/commercial/add-cardholder", body).get("data");
        String customerId = data == null ? null : text(data, "customerId");
        if (customerId == null || customerId.isEmpty()) {
            throw new PlatformException("missing customerId in response", null, false);
        }
        return customerId;
    }

    /**
     * 开卡。生产环境应先 INSERT 本地单(requestNo=CREATED) 再调用。
     *
     * @return state + data（data 中始终带回 requestNo，供查单）
     */
    public OpenCardResult openCardPrepaidVirtual(String customerId, String productCode) throws Exception {
        String requestNo = newRequestNo("open");
        Map<String, Object> body = new HashMap<>();
        body.put("requestNo", requestNo);
        body.put("secretKey", secretKey);
        body.put("ip", "127.0.0.1");
        body.put("customerId", customerId);
        body.put("cardProductCode", productCode);
        body.put("cardType", "V");
        body.put("accountMode", 1);

        try {
            JsonNode payload = client.postAndParse("/rest/v2.0/api/common/openCard", body);
            JsonNode data = payload.get("data");
            LocalOpenCardState state = mapOpenCardStatus(data == null ? null : text(data, "openCardStatus"));
            return new OpenCardResult(state, data, requestNo, null);
        } catch (TransportException e) {
            // 未知：进入查单，不要直接再 open
            return new OpenCardResult(LocalOpenCardState.UNKNOWN, null, requestNo, e.getMessage());
        } catch (PlatformException e) {
            if (e.isRetryable()) {
                return new OpenCardResult(LocalOpenCardState.UNKNOWN, null, requestNo, e.getMessage());
            }
            return new OpenCardResult(LocalOpenCardState.FAIL, null, requestNo, e.getMessage());
        }
    }

    /** 开卡状态查询：必填 originalRequestNo = 开卡时的 requestNo。 */
    public OpenCardResult queryOpenCard(String originalRequestNo) throws Exception {
        Map<String, Object> body = new HashMap<>();
        body.put("requestNo", newRequestNo("oq"));
        body.put("secretKey", secretKey);
        body.put("ip", "127.0.0.1");
        body.put("originalRequestNo", originalRequestNo);
        JsonNode payload = client.postAndParse("/rest/v2.0/api/common/openCardQuery", body);
        JsonNode data = payload.get("data");
        if (data != null && data.isArray() && data.size() > 0) {
            data = data.get(0);
        }
        String status = data == null ? null : firstNonNull(text(data, "openCardStatus"), text(data, "status"));
        return new OpenCardResult(mapOpenCardStatus(status), data, originalRequestNo, null);
    }

    /** 指数退避查单直到终态或次数用尽。 */
    public OpenCardResult waitTerminal(String originalRequestNo, int maxAttempts, long baseSleepMs)
            throws Exception {
        OpenCardResult last = null;
        long sleep = baseSleepMs;
        for (int i = 0; i < maxAttempts; i++) {
            last = queryOpenCard(originalRequestNo);
            if (last.state() == LocalOpenCardState.SUCCESS || last.state() == LocalOpenCardState.FAIL) {
                return last;
            }
            Thread.sleep(sleep);
            sleep = Math.min((long) (sleep * 1.8), 30_000L);
        }
        return last == null
                ? new OpenCardResult(LocalOpenCardState.PENDING, null, originalRequestNo, null)
                : new OpenCardResult(LocalOpenCardState.PENDING, last.data(), originalRequestNo, null);
    }

    public static LocalOpenCardState mapOpenCardStatus(String raw) {
        if (raw == null) {
            return LocalOpenCardState.UNKNOWN;
        }
        return switch (raw.toUpperCase(Locale.ROOT)) {
            case "SUCCESS" -> LocalOpenCardState.SUCCESS;
            case "FAIL" -> LocalOpenCardState.FAIL;
            case "PENDING" -> LocalOpenCardState.PENDING;
            default -> LocalOpenCardState.UNKNOWN;
        };
    }

    public record OpenCardResult(
            LocalOpenCardState state,
            JsonNode data,
            String requestNo,
            String error
    ) {}

    public static void main(String[] args) throws Exception {
        String env = env("KUN_ENV", "sandbox");
        String appKey = requireEnv("KUN_APP_KEY");
        String customerNo = requireEnv("KUN_CUSTOMER_NO");
        String secretKey = requireEnv("KUN_SECRET_KEY");
        Path privateKey = Path.of(requireEnv("KUN_PRIVATE_KEY"));
        String productCode = env("KUN_CARD_PRODUCT_CODE", "");

        KunOpenApiClient client = new KunOpenApiClient(env, appKey, customerNo, privateKey);
        CommercialPrepaidFlow flow = new CommercialPrepaidFlow(client, secretKey, productCode);

        if (productCode.isEmpty()) {
            List<JsonNode> products = flow.listCommercialVirtualProducts();
            if (products.isEmpty()) {
                System.err.println("no COMMERCIAL+V product; set KUN_CARD_PRODUCT_CODE");
                System.exit(1);
            }
            productCode = text(products.get(0), "cardProductCode");
            System.out.println("picked product: " + productCode
                    + " modes: " + text(products.get(0), "supportedCardModes"));
        }

        String customerId = flow.addCardholder("San", "Zhang", "demo.holder@example.com");
        System.out.println("customerId: " + customerId);

        OpenCardResult result = flow.openCardPrepaidVirtual(customerId, productCode);
        System.out.println("open sync state: " + result.state());

        if (result.state() == LocalOpenCardState.PENDING || result.state() == LocalOpenCardState.UNKNOWN) {
            result = flow.waitTerminal(result.requestNo(), 10, 2000L);
            System.out.println("after poll: " + result.state());
        }

        if (result.state() == LocalOpenCardState.SUCCESS) {
            JsonNode d = result.data();
            System.out.println("DONE cardId=" + (d == null ? null : text(d, "cardId"))
                    + " accountNo=" + (d == null ? null : text(d, "accountNo")));
        } else if (result.state() == LocalOpenCardState.FAIL) {
            System.err.println("FAIL — fix params then retry with NEW requestNo; do not reuse");
            System.exit(2);
        } else {
            System.err.println("STILL PENDING — schedule job to keep querying; do not re-open");
            System.exit(3);
        }
    }

    private static String env(String k, String def) {
        String v = System.getenv(k);
        return v == null || v.isEmpty() ? def : v;
    }

    private static String requireEnv(String k) {
        String v = System.getenv(k);
        if (v == null || v.isEmpty()) {
            throw new IllegalStateException("missing env " + k);
        }
        return v;
    }

    private static String text(JsonNode n, String field) {
        if (n == null) {
            return null;
        }
        JsonNode v = n.get(field);
        return v == null || v.isNull() ? null : v.asText();
    }

    private static String firstNonNull(String a, String b) {
        return a != null ? a : b;
    }
}
