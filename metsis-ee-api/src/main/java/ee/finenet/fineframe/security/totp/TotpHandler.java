package ee.finenet.fineframe.security.totp;

import org.apache.commons.codec.binary.Base32;

import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Date;
import java.util.concurrent.TimeUnit;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public class TotpHandler {

    private static final Base32 BASE_32 = new Base32();
    private static final String HMAC_SHA_1 = "HmacSHA1";
    private static SecureRandom random = new SecureRandom();
    private final static int SECRET_SIZE = 16;

    public static String createSharedKey() {
        byte[] secretKey = new byte[SECRET_SIZE];
        random.nextBytes(secretKey);
        return new String(BASE_32.encode(secretKey), StandardCharsets.UTF_8).substring(0, 26);
    }

    public static boolean isCorrectTOTPCode(String secret, long code) {
        if (secret == null) {
            return false;
        }
        long t = new Date().getTime() / TimeUnit.SECONDS.toMillis(30);
        byte[] decodedKey = BASE_32.decode(secret);

        // Window is used to check codes generated in the near past.
        // You can use this value to tune how far you're willing to go.
        int window = 3;
        for (int i = -window; i <= window; ++i) {
            long hash;
            try {
                hash = verifyCode(decodedKey, t + i);
            } catch (Exception e) {
                return false;
            }
            if (hash == code) {
                return true;
            }
        }
        // The validation code is invalid.
        return false;
    }

    private static int verifyCode(byte[] key, long t) throws NoSuchAlgorithmException, InvalidKeyException {
        byte[] data = new byte[8];
        long value = t;
        for (int i = 8; i-- > 0; value >>>= 8) {
            data[i] = (byte) value;
        }


        SecretKeySpec signKey = new SecretKeySpec(key, HMAC_SHA_1);
        Mac mac = Mac.getInstance(HMAC_SHA_1);
        mac.init(signKey);
        byte[] hash = mac.doFinal(data);


        int offset = hash[20 - 1] & 0xF;

        // We're using a long because Java hasn't got unsigned int.
        long truncatedHash = 0;
        for (int i = 0; i < 4; ++i) {
            truncatedHash <<= 8;
            // We are dealing with signed bytes:
            // we just keep the first byte.
            truncatedHash |= (hash[offset + i] & 0xFF);
        }
        truncatedHash &= 0x7FFFFFFF;
        truncatedHash %= 1000000;
        return (int) truncatedHash;
    }
}
