package com.kun.card.integration;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.Signature;
import java.security.spec.PKCS8EncodedKeySpec;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/**
 * KUN 开放平台轻量客户端：RSA SHA256withRSA 签名 + POST。
 * 签名规则见开放文档「鉴权认证机制」。
 */
public final class KunOpenApiClient {

    public static final String SANDBOX = "https://sandbox.kun.global";
    public static final String PRODUCTION = "https://openapi.kun.global";

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final String baseUrl;
    private final String appKey;
    private final String customerNo;
    private final PrivateKey privateKey;
    private final HttpClient http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(15))
            .build();

    public KunOpenApiClient(String env, String appKey, String customerNo, Path privateKeyPem) throws Exception {
        this.baseUrl = "production".equalsIgnoreCase(env) ? PRODUCTION : SANDBOX;
        this.appKey = appKey;
        this.customerNo = customerNo;
        this.privateKey = loadPrivateKey(privateKeyPem);
    }

    public ApiResponse post(String path, Map<String, Object> body) throws Exception {
        String json = MAPPER.writeValueAsString(body);
        String timestamp = String.valueOf(System.currentTimeMillis());

        Map<String, String> signParams = new TreeMap<>();
        ObjectNode node = (ObjectNode) MAPPER.readTree(json);
        Iterator<Map.Entry<String, JsonNode>> fields = node.fields();
        while (fields.hasNext()) {
            Map.Entry<String, JsonNode> e = fields.next();
            signParams.put(e.getKey().toLowerCase(Locale.ROOT), valueForSign(e.getValue()));
        }
        signParams.put("customerno", customerNo);
        signParams.put("timestamp", timestamp);

        String signString = buildSignString(signParams);
        String sign = signSha256Rsa(signString);

        String url = baseUrl + (path.startsWith("/") ? path : "/" + path);
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json; charset=UTF-8")
                .header("App-Key", appKey)
                .header("Api-Version", "2")
                .header("Customer-No", customerNo)
                .header("Timestamp", timestamp)
                .header("Sign", sign)
                .POST(HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8))
                .build();

        try {
            HttpResponse<String> resp = http.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            return new ApiResponse(resp.statusCode(), resp.body());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new TransportException("interrupted", e);
        } catch (Exception e) {
            throw new TransportException("transport error: " + e.getMessage(), e);
        }
    }

    public JsonNode postAndParse(String path, Map<String, Object> body) throws Exception {
        ApiResponse resp = post(path, body);
        if (resp.statusCode() >= 500) {
            throw new PlatformException("HTTP " + resp.statusCode(), null, true);
        }
        if (resp.statusCode() >= 400) {
            throw new PlatformException("HTTP " + resp.statusCode() + ": " + truncate(resp.body()), null, false);
        }
        JsonNode payload;
        try {
            payload = MAPPER.readTree(resp.body());
        } catch (Exception e) {
            throw new PlatformException("invalid json: " + e.getMessage(), null, true);
        }
        String code = text(payload, "code");
        if (code != null && !code.isEmpty()
                && !"0000".equals(code) && !"0".equals(code) && !"SUCCESS".equalsIgnoreCase(code)) {
            // 策略见 references/产品能力/异常码处理.md：
            // KLC0005/0013/9600/9999/0009/0010 → retryable，上层只查单/幂等，勿盲重开
            boolean retryable = isQueryFirstCode(code);
            throw new PlatformException(
                    "platform code=" + code + " message=" + text(payload, "message"),
                    code,
                    retryable);
        }
        return payload;
    }

    /** 系统繁忙/超时/未知/重复/待处理：优先查单或幂等，不直接换新单重开。 */
    private static boolean isQueryFirstCode(String code) {
        return "KLC0005".equals(code)
                || "KLC0013".equals(code)
                || "KLC0018".equals(code)
                || "KLC9600".equals(code)
                || "KLC9999".equals(code)
                || "KLC0009".equals(code)
                || "KLC0010".equals(code);
    }

    private static String valueForSign(JsonNode v) throws Exception {
        if (v == null || v.isNull()) {
            return "";
        }
        if (v.isObject() || v.isArray()) {
            return MAPPER.writeValueAsString(v);
        }
        if (v.isBoolean()) {
            return v.booleanValue() ? "true" : "false";
        }
        return v.asText();
    }

    private static String buildSignString(Map<String, String> params) {
        List<String> parts = new ArrayList<>();
        for (Map.Entry<String, String> e : params.entrySet()) {
            if ("sign".equals(e.getKey())) {
                continue;
            }
            parts.add(e.getKey() + "=" + urlEncode(e.getValue() == null ? "" : e.getValue()));
        }
        return String.join("&", parts);
    }

    /** 与文档一致：UTF-8 URL encode；空格为 %20 而非 +。 */
    private static String urlEncode(String raw) {
        return URLEncoder.encode(raw, StandardCharsets.UTF_8).replace("+", "%20");
    }

    private String signSha256Rsa(String signString) throws Exception {
        Signature signature = Signature.getInstance("SHA256withRSA");
        signature.initSign(privateKey);
        signature.update(signString.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(signature.sign());
    }

    private static PrivateKey loadPrivateKey(Path pemPath) throws Exception {
        String pem = Files.readString(pemPath);
        String normalized = pem
                .replace("-----BEGIN PRIVATE KEY-----", "")
                .replace("-----END PRIVATE KEY-----", "")
                .replace("-----BEGIN RSA PRIVATE KEY-----", "")
                .replace("-----END RSA PRIVATE KEY-----", "")
                .replaceAll("\\s", "");
        byte[] der = Base64.getDecoder().decode(normalized);
        return KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(der));
    }

    private static String text(JsonNode n, String field) {
        JsonNode v = n.get(field);
        return v == null || v.isNull() ? null : v.asText();
    }

    private static String truncate(String s) {
        if (s == null) {
            return "";
        }
        return s.length() <= 200 ? s : s.substring(0, 200);
    }

    public record ApiResponse(int statusCode, String body) {}

    /** 传输层失败：超时、连接、5xx、无法解析 → 视为未知，只查单。 */
    public static class TransportException extends Exception {
        public TransportException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    /** 平台层明确失败（鉴权/参数等）；retryable=false 时勿盲重试同 requestNo 写操作。 */
    public static class PlatformException extends Exception {
        private final String code;
        private final boolean retryable;

        public PlatformException(String message, String code, boolean retryable) {
            super(message);
            this.code = code;
            this.retryable = retryable;
        }

        public String getCode() {
            return code;
        }

        public boolean isRetryable() {
            return retryable;
        }
    }
}
