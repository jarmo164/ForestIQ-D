package ee.finenet.fineframe.http;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(RetentionPolicy.RUNTIME)
public @interface Requestable {
    RequestMethod method() default RequestMethod.GET;
    String value();
    boolean secured() default true;
}
