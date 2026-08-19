package ee.finenet.fineframe.http;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.exceptions.ConfigurationException;
import ee.finenet.fineframe.exceptions.FineFrameException;
import ee.finenet.fineframe.exceptions.ForbiddenException;
import ee.finenet.fineframe.exceptions.ResourceNotFoundException;
import ee.finenet.fineframe.exceptions.UnauthorizedException;
import ee.finenet.fineframe.exceptions.UnexpextedException;
import ee.finenet.fineframe.http.genericmodels.ErrorModel;
import ee.finenet.fineframe.security.token.AuthTokenValidationFilter;
import ee.finenet.fineframe.security.token.Jwt;
import ee.finenet.fineframe.security.token.WebSocketAuthenticator;
import ee.finenet.fineframe.serialization.GsonHolder;
import org.eclipse.jetty.http.HttpStatus;
import org.reflections.Reflections;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.Set;

import static spark.Spark.before;
import static spark.Spark.delete;
import static spark.Spark.exception;
import static spark.Spark.get;
import static spark.Spark.port;
import static spark.Spark.post;
import static spark.Spark.put;
import static spark.Spark.webSocket;

public class FineFrameBootstrap {

    private static final Logger logger = LoggerFactory.getLogger(ee.finenet.fineframe.http.FineFrameBootstrap.class);

    private static final String WEBSOCKETS_PREFIX = "/ws";
    private static final String API_URL_PREFIX = "/api";
    private static final String SECURED_AREA_PREFIX = "/services";

    public static void initialize(String requestHandlersRootPackage, Object serviceRegistry, Class<?> serviceRegistryClass, Jwt jwt, int portNumber) {
        port(portNumber);
        exceptionHandling();
        activateWebSockets(requestHandlersRootPackage, serviceRegistryClass, serviceRegistry, jwt);
        setUpAuth(jwt);
        setContentTypeToJson();
        initializeRequestHandlers(requestHandlersRootPackage, serviceRegistry, serviceRegistryClass);
    }

    private static void activateWebSockets(String requestHandlersRootPackage, Class<?> serviceRegistryClass, Object serviceRegistry, Jwt jwt) {
        logger.info("Initializing websocket handlers");
        Set<Class<?>> wsHandlers = new Reflections(requestHandlersRootPackage).getTypesAnnotatedWith(WSPath.class);
        for (Class<?> wsHandler : wsHandlers) {
            String wsPath = wsHandler.getAnnotation(WSPath.class).value();
            String path = WEBSOCKETS_PREFIX + wsPath;
            try {
                webSocket(path,  wsHandler.getConstructor(WebSocketAuthenticator.class, serviceRegistryClass).newInstance(new WebSocketAuthenticator(jwt), serviceRegistry));
            } catch (Exception e) {
                throw new FineFrameException("Registering websocket failed", e);
            }
            logger.info("WSHandler {} activated to serve on path {}", wsHandler, path);
        }
    }

    private static void initializeRequestHandlers(String requestHandlersRootPackage, Object serviceRegistry, Class<?> serviceRegistryClass) {
        Set<Class<?>> requestHandlers = new Reflections(requestHandlersRootPackage).getTypesAnnotatedWith(Requestable.class);
        for (Class<?> requestHandler : requestHandlers) {
            if (RequestHandler.class.isAssignableFrom(requestHandler)) {
                try {
                    Constructor<?> constructor = requestHandler.getConstructor(serviceRegistryClass);
                    RequestHandler handlerInstace = (RequestHandler) constructor.newInstance(serviceRegistry);
                    Requestable requestableAnnotation = requestHandler.getAnnotation(Requestable.class);
                    if (requestableAnnotation == null) {
                        throw new IllegalStateException(String.format("%s is missing @Requestable annotation", requestHandler));
                    }
                    String path = requestableAnnotation.value();
                    boolean secured = requestableAnnotation.secured();
                    if (secured) {
                        path = API_URL_PREFIX + SECURED_AREA_PREFIX + path;
                    } else {
                        path = API_URL_PREFIX + path;
                    }
                    RequestMethod requestMethod = requestableAnnotation.method();
                    if (requestMethod == RequestMethod.GET) {
                        get(path, handlerInstace::handle, GsonHolder.GSON::toJson);
                    } else if (requestMethod == RequestMethod.POST) {
                        post(path, handlerInstace::handle, GsonHolder.GSON::toJson);
                    } else if (requestMethod == RequestMethod.PUT) {
                        put(path, handlerInstace::handle, GsonHolder.GSON::toJson);
                    } else if (requestMethod == RequestMethod.DELETE) {
                        delete(path, handlerInstace::handle, GsonHolder.GSON::toJson);
                    } else {
                        throw new ConfigurationException(String.format("RequestHandler %s had unknown request type: %s", requestHandler, requestMethod));
                    }
                    logger.info("Requesthandler {} activated to serve requests from path {}", requestHandler, path);
                } catch (IllegalAccessException | InstantiationException | NoSuchMethodException | InvocationTargetException e) {
                    throw new UnexpextedException(String.format("Instantiating request handler %s failed", requestHandler), e);
                }
            } else {
                throw new UnexpextedException(String.format("@Requestable annotation was put on illegal class %s.", requestHandler));
            }
        }
        get(WEBSOCKETS_PREFIX + "/api", new NotFoundHandler()::handle, GsonHolder.GSON::toJson);
    }

    private static void setUpAuth(Jwt jwt) {
        AuthTokenValidationFilter authTokenFilter = new AuthTokenValidationFilter(jwt);
        before(API_URL_PREFIX + SECURED_AREA_PREFIX + "/*", authTokenFilter);
    }

    private static void setContentTypeToJson() {
        before((request, response) -> response.type("application/json"));
    }

    private static void exceptionHandling() {
        exception(Exception.class, (exception, request, response) -> {
            if (exception instanceof ForbiddenException) {
                response.status(HttpStatus.FORBIDDEN_403);
                response.body(GsonHolder.GSON.toJson(new ErrorModel((ForbiddenException) exception)));
                logger.info(exception.getMessage());
            } else if (exception instanceof BadRequestException) {
                response.status(HttpStatus.BAD_REQUEST_400);
                response.body(GsonHolder.GSON.toJson(new ErrorModel((BadRequestException) exception)));
                logger.info(exception.getMessage());
            } else if (exception instanceof ResourceNotFoundException) {
                response.status(HttpStatus.NOT_FOUND_404);
                response.body(GsonHolder.GSON.toJson(new ErrorModel((ResourceNotFoundException) exception)));
                logger.info(exception.getMessage());
            } else if (exception instanceof UnauthorizedException) {
                response.status(HttpStatus.UNAUTHORIZED_401);
                response.body(GsonHolder.GSON.toJson(new ErrorModel((UnauthorizedException) exception)));
                logger.info(exception.getMessage());
            } else if (exception instanceof FineFrameException) {
                response.status(HttpStatus.INTERNAL_SERVER_ERROR_500);
                response.body(GsonHolder.GSON.toJson(new ErrorModel((FineFrameException) exception)));
                logger.error("Unexpected exception", exception);
            } else {
                response.status(HttpStatus.INTERNAL_SERVER_ERROR_500);
                response.body(GsonHolder.GSON.toJson(new ErrorModel()));
                logger.error("Unexpected exception", exception);
            }
        });
    }
}
