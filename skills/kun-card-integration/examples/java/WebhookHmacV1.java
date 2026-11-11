package com.kun.card.integration;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

/**
 * Webhook HMAC-SHA256 v1 验签（与平台出站签名一致）。
 *
 * <pre>
 * signing_string = "{timestamp}.{rawBody}"
 * signature      = lowercase_hex(HMAC_SHA256(secret_utf8, signing_string_utf8))
 * </pre>
 *
 * Headers: {@code X-Webhook-Timestamp}, {@code X-Webhook-Signature}（纯 hex 或 {@code v1=&lt;hex&gt;}）。
 * rawBody 必须是 HTTP 原文，不要 JSON 重排/再序列化。
 */
public final class WebhookHmacV1 {

    public static final String HEADER_TIMESTAMP = "X-Webhook-Timestamp";
    public static final String HEADER_SIGNATURE = "X-Webhook-Signature";

    private WebhookHmacV1() {
    }

    public static String signV1Hex(String secret, long timestampSeconds, String rawBody) {
        Objects.requireNonNull(secret, "secret");
        Objects.requireNonNull(rawBody, "rawBody");
        String signingString = timestampSeconds + "." + rawBody;
        byte[] mac = hmacSha256(secret.getBytes(StandardCharsets.UTF_8),
                signingString.getBytes(StandardCharsets.UTF_8));
        return toHexLower(mac);
    }

    public static VerifyResult verifyV1Hex(String secret, long timestampSeconds, String rawBody,
                                           String signatureHeaderValue, long toleranceSeconds) {
        if (secret == null || secret.isEmpty()) {
            return VerifyResult.fail("missing_secret");
        }
        if (rawBody == null) {
            return VerifyResult.fail("missing_body");
        }
        if (signatureHeaderValue == null || signatureHeaderValue.isEmpty()) {
            return VerifyResult.fail("missing_signature");
        }
        if (toleranceSeconds <= 0) {
            toleranceSeconds = 300;
        }
        long now = Instant.now().getEpochSecond();
        if (Math.abs(now - timestampSeconds) > toleranceSeconds) {
            return VerifyResult.fail("timestamp_out_of_range");
        }
        String provided = normalizeSignature(signatureHeaderValue);
        if (provided.isEmpty()) {
            return VerifyResult.fail("bad_signature_format");
        }
        String expected = signV1Hex(secret, timestampSeconds, rawBody);
        if (!constantTimeEquals(expected, provided)) {
            return VerifyResult.fail("signature_mismatch");
        }
        return VerifyResult.ok();
    }

    /**
     * 从 header map 验签（key 大小写不敏感）。
     */
    public static VerifyResult verifyFromHeaders(String secret, Map<String, String> headers,
                                                 String rawBody, long toleranceSeconds) {
        String tsRaw = headerIgnoreCase(headers, HEADER_TIMESTAMP);
        String sig = headerIgnoreCase(headers, HEADER_SIGNATURE);
        if (tsRaw == null || tsRaw.isEmpty()) {
            return VerifyResult.fail("missing_timestamp");
        }
        long ts;
        try {
            ts = Long.parseLong(tsRaw.trim());
        } catch (NumberFormatException e) {
            return VerifyResult.fail("bad_timestamp");
        }
        return verifyV1Hex(secret, ts, rawBody, sig == null ? "" : sig, toleranceSeconds);
    }

    private static String headerIgnoreCase(Map<String, String> headers, String name) {
        if (headers == null) {
            return null;
        }
        for (Map.Entry<String, String> e : headers.entrySet()) {
            if (e.getKey() != null && e.getKey().equalsIgnoreCase(name)) {
                return e.getValue();
            }
        }
        return null;
    }

    private static String normalizeSignature(String signatureHeaderValue) {
        String s = signatureHeaderValue.trim();
        int idx = s.indexOf('=');
        if (idx > 0) {
            String prefix = s.substring(0, idx).trim().toLowerCase(Locale.ROOT);
            String val = s.substring(idx + 1).trim();
            if (!"v1".equals(prefix)) {
                return "";
            }
            s = val;
        }
        return s.replace(" ", "").toLowerCase(Locale.ROOT);
    }

    private static byte[] hmacSha256(byte[] key, byte[] message) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(key, "HmacSHA256"));
            return mac.doFinal(message);
        } catch (Exception e) {
            throw new IllegalStateException("HMAC-SHA256 failed", e);
        }
    }

    private static String toHexLower(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(String.format(Locale.ROOT, "%02x", b));
        }
        return sb.toString();
    }

    private static boolean constantTimeEquals(String a, String b) {
        if (a == null || b == null || a.length() != b.length()) {
            return false;
        }
        int r = 0;
        for (int i = 0; i < a.length(); i++) {
            r |= a.charAt(i) ^ b.charAt(i);
        }
        return r == 0;
    }

    public static final class VerifyResult {
        private final boolean ok;
        private final String reason;

        private VerifyResult(boolean ok, String reason) {
            this.ok = ok;
            this.reason = reason;
        }

        public static VerifyResult ok() {
            return new VerifyResult(true, "ok");
        }

        public static VerifyResult fail(String reason) {
            return new VerifyResult(false, reason);
        }

        public boolean isOk() {
            return ok;
        }

        public String getReason() {
            return reason;
        }
    }
}
