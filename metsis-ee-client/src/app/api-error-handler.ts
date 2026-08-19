import {ErrorObservable} from 'rxjs/observable/ErrorObservable';
import {Injectable} from '@angular/core';
import {ApiError} from './api.error';
import {ApiErrorCode} from './api.error.code';

@Injectable()
export class ApiErrorHandler {

  static translations = {};

  constructor() {
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAIL_NO_USERNAME] = 'Username was not provided. Please provide username.';
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAIL_NO_PASSWORD] = 'Password was not provided. Please provide password.';
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAIL_NO_TOKEN] = 'Token was not provided.';
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAIL_INVALID_TOKEN] = 'Provided token was not valid.';
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAIL_NO_SUCH_USER] = 'No user with provided username.';
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAIL_WRONG_PASSWORD] = 'Provided password was wrong.';
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAILED_TOTP_OFF] = 'Two factor authentication is not enabled for user.';
    ApiErrorHandler.translations[ApiErrorCode.AUTH_FAILED_WRONG_TOTP_CODE] = 'Provided two factor authentication code was wrong.';
    ApiErrorHandler.translations[ApiErrorCode.DB_ERROR] = 'Communication with database failed';
    ApiErrorHandler.translations[ApiErrorCode.UNKNOWN_ERROR] = 'Unexpected error occured. Please contact the administrator.';
    ApiErrorHandler.translations[ApiErrorCode.NOT_ENOUGH_PRIVILEGES] = 'User does not have enough privileged to access the given resource.';
    ApiErrorHandler.translations[ApiErrorCode.SERVICE_NOT_FOUND] = 'Requested service does not exist.';
    ApiErrorHandler.translations[ApiErrorCode.ADMIN_SET_USER_PRIVILEGES_USERNAME_NOT_SET] = 'Can not save privileges for unset user.';
    ApiErrorHandler.translations[ApiErrorCode.ADMIN_ADD_USER_INVALID_ID] = 'Invalid username. Username is mandatory. Its length must be between 4 and 50 characters, it must be fully lowercase and contain only english characters and numbers.';
    ApiErrorHandler.translations[ApiErrorCode.ADMIN_ADD_USER_USER_ALREADY_EXISTS] = 'User with the chosen username already exists.';
    ApiErrorHandler.translations[ApiErrorCode.ADMIN_ADD_USER_INVALID_FULL_NAME] = 'Invalid full name. Full name is mandatory. Its length must be between 4 and 100 characters.';
    ApiErrorHandler.translations[ApiErrorCode.NO_SUCH_USER] = 'Provided user was not found.';
    ApiErrorHandler.translations[ApiErrorCode.CHANGE_MY_PASSWORD_WRONG_OLD_PASSWORD] = 'Provided old password is wrong.';
    ApiErrorHandler.translations[ApiErrorCode.CHANGE_MY_PASSWORD_NEW_PASSWORD_INVALID] = 'New password does not meet preconditions. It must contain at least one lowercase and one uppercase character and at least one number. It must be at least 8 characters long.';
    ApiErrorHandler.translations[ApiErrorCode.CHANGE_MY_PASSWORD_NEW_PASSWORD_NEW_PASSWORD_AGAIN_MISMATCH] = 'New password field does not match with new password again field.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_NOT_FOUND] = 'Could not find owner.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_NAME_EMPTY] = 'Owner name must not be empty';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_NAME_TOO_LONG] = 'Owner name can be up to 100 characters long';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_PHONE_TOO_LONG] = 'Owner phone must not be longer than 100 characters.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_EMAIL_TOO_LONG] = 'Owner email must not be longer than 100 characters.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_ADDRESS_TOO_LONG] = 'Owner address must not be longer than 500 characters.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_TYPE_TOO_LONG] = 'Owner type must not be longer than 20 characters.';
    ApiErrorHandler.translations[ApiErrorCode.CADASTRE_NOT_FOUND] = 'Cadastre not found';
    ApiErrorHandler.translations[ApiErrorCode.ADMIN_ASSIGN_WORK_TO_CALLER_NO_ASSIGNEE] = 'Assignee must be selected before assigning work.';
    ApiErrorHandler.translations[ApiErrorCode.ADMIN_ASSIGN_WORK_TO_CALLER_NO_SUCH_ASSIGNEE] = 'Selected assignee does not exist.';
    ApiErrorHandler.translations[ApiErrorCode.ADMIN_ASSIGN_WORK_TO_CALLER_NO_OWNERS] = 'No owners were selected for assigning.';
    ApiErrorHandler.translations[ApiErrorCode.UNKNOWN_OWNER_STATUS] = 'Unknown owner status.';
    ApiErrorHandler.translations[ApiErrorCode.EMPTY_LOG_MESSGE_NOT_ALLOWED] = 'Empty log message not allowed.';
    ApiErrorHandler.translations[ApiErrorCode.MARK_CADASTRES_ONE_OF_SUPPLIED_CADASTRES_NOT_SUPPLIED_OWNERS] = 'One of marked cadastres does not belong to supplied owner.';
    ApiErrorHandler.translations[ApiErrorCode.CAN_NOT_REASSIGN_WORK_FROM_USER_TO_ITSELF] = 'Can not reassign work to user who it was already assigned';
    ApiErrorHandler.translations[ApiErrorCode.CANT_DOUBLE_ASSIGN_CADASTRE_LABEL] = 'Cadastre already has this label';
    ApiErrorHandler.translations[ApiErrorCode.UNKNOWN_CADASTRE_LABEL] = 'Unknown cadastre label';
    ApiErrorHandler.translations[ApiErrorCode.CAN_NOT_DELETE_USER_HAS_ASSIGNED_OWNERS] = 'Can not delete user as it has assigned owners. Reassig all its owners from admin workdesk and try again.';
    ApiErrorHandler.translations[ApiErrorCode.USER_STATISTICS_SEARCH_NEEDS_AT_LEAST_ONE_FROM_STATUS] = 'User statistics search needs at least one "From status" as an input.';
    ApiErrorHandler.translations[ApiErrorCode.USER_STATISTICS_SEARCH_NEEDS_AT_LEAST_ONE_TO_STATUS] = 'User statistics search needs at least one "To status" as an input.';
    ApiErrorHandler.translations[ApiErrorCode.USER_STATISTICS_SEARCH_NEEDS_SINCE_DATE] = 'User statistics search needs "Since Date" as an input.';
    ApiErrorHandler.translations[ApiErrorCode.USER_STATISTICS_SEARCH_NEEDS_GRANULARITY] = 'User statistics search needs "Granularity" as an input.';
    ApiErrorHandler.translations[ApiErrorCode.USER_STATISTICS_SEARCH_NEEDS_AT_LEAST_ONE_USER] = 'User statistics search needs at least one user as an input.';
    ApiErrorHandler.translations[ApiErrorCode.USER_STATISTICS_SEARCH_UPTO_DATE_NEEDS_TO_BE_AFTER_SINCE_DATE] = 'Up to date needs to be after since date.';
    ApiErrorHandler.translations[ApiErrorCode.NO_MORE_WORK_ASSIGNED_OWNERS_FOR_AUTHENTICATED_USER] = 'There is no assigned owners on the authenticated users name.';
    ApiErrorHandler.translations[ApiErrorCode.CAN_NOT_REFRESH_OWNER_OWNING_RELATIONS_FROM_RIK_URL_NOT_PARSABLE] = 'RIK owner-property update failed. Properties not parsable from URL.';
    ApiErrorHandler.translations[ApiErrorCode.UNABLE_TO_CONNECT_TO_RIK_SERVICE] = 'Unable to connect to RIK service.';
    ApiErrorHandler.translations[ApiErrorCode.ADD_OWNER_BLANK_OWNER_NAME_NOT_ALLOWED] = 'Owner name must not be blank.';
    ApiErrorHandler.translations[ApiErrorCode.ADD_OWNER_OWNER_NAME_TOO_LONG] = 'Owner name must up to 100 characters long.';
    ApiErrorHandler.translations[ApiErrorCode.ADD_OWNER_OWNER_ID_TOO_LONG] = 'Owner ID must be up to 50 characters long.';
    ApiErrorHandler.translations[ApiErrorCode.ADD_OWNER_ONLY_NUMBERS_ALLOWED] = 'Only numbers are allowed in owner ID.';
    ApiErrorHandler.translations[ApiErrorCode.ADD_OWNER_OWNER_ALREADY_EXISTS] = 'Owner with this ID already exists.';
    ApiErrorHandler.translations[ApiErrorCode.CONTRACT_NOT_FOUND] = 'Contract with given ID was not found.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_INPUT_NO_SELLER_HAS_PHONE_NO] = 'At least one seller must have phone number set.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_INVALID_TEMPLATE_NUMBER] = 'Invalid template number.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_INPUT_UNKNOWN_WORK_TYPE] = 'Unknown type of work.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_INVALID_TEMPLATE_NUMBER] = 'Invalid template type.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_CONTRACT_NR_MISSING] = 'Contract number is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BUYER_CODE_MISSING] = 'Buyer code is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BUYER_NAME_MISSING] = 'Buyer name is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BUYER_ADDRESS_IS_MISSING] = 'Buyer address is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BUYER_EMAIL_IS_MISSING] = 'Buyer email is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BUYER_PHONE_IS_MISSING] = 'Buyer phone is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BUYER_PROXY_CODE_IS_MISSING] = 'Buyer proxy code is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BUYER_PROXY_NAME_IS_MISSING] = 'Buyer proxy name is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_NO_SELLERS] = 'Contract must have at least one seller.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_SELLER_CODE_MISSING] = 'There is a seller with a missing code.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_SELLER_NAME_MISSING] = 'There is a seller with a missing name.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_SELLER_PROXY_CODE_IS_MISSING] = 'There is a seller which has a proxy, but the proxy code is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_SELLER_PROXY_NAME_IS_MISSING] = 'There is a seller which has a proxy, but the proxy name is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_PRICE_MUST_BE_POSITIVE] = 'Sales price must be positive.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_DATE_OF_ENFORCEMENT_MISSING] = 'Date of enforcement is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_FINAL_DATE_MISSING] = 'Final date is missing.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_FINAL_DATE_BEFORE_DATE_OF_ENFORCEMENT] = 'Final date must be after date of enforcement.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_BANK_DAYS_TO_PAY_UP_MUST_BE_POSITIVE] = 'Bank days to pay up must be positive';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_WRITTEN_PRICE_MISSING] = 'Written price is missing';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_CADASTRES_EMPTY] = 'Contract must have at least one cadastre.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_CADASTRE_ID_MISSING] = 'There is a cadastre with a missing ID.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_CADASTRE_ADDRESS_MISSING] = 'There is a cadastre with a missing address.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_NO_FOREST_SECTIONS] = 'There is a cadastre without forrest sections. Even if there is no forest plan, please still add forest sections to represent type of works to be done on the land.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_FOREST_SECTION_ID_MISSING] = 'There is a cadastre with a missing forrest section ID.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_FOREST_SECTION_TYPE_OF_WORK_MISSING] = 'There is a cadastre with a forrest section which is missing type of work.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_SELLER_BANK_ACCOUNT_NR_IS_MISSING] = 'There is a seller with missing bank account number.';
    ApiErrorHandler.translations[ApiErrorCode.ILLEGAL_CONTRACT_SELLER_MONEY_OBTAINED_FROM_THE_DEAL_MISSING] = 'There is a seller with missing amount to be payed.';
    ApiErrorHandler.translations[ApiErrorCode.NO_SUCH_OWNER_STATUS] = 'No owner status found with given code';
    ApiErrorHandler.translations[ApiErrorCode.OWNERS_EXIST_WITH_GIVEN_STATUS] = 'There are existing owners who actively use this status. Can not delete it.';
    ApiErrorHandler.translations[ApiErrorCode.CAN_NOT_DELETE_PROTECTED_STATUS] = 'This is a protected status. Can not delete it.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_STATUS_SAVE_NO_MODEL] = 'No model for status save';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_STATUS_SAVE_NO_COLOR] = 'Must pick a color for status.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_STATUS_SAVE_INVALID_COLOR] = 'Status color has to be a 6 digit HEX code.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_STATUS_SAVE_INVALID_DURATION_DAYS] = 'Duration days must be bigger than 0 and less than 50000.';
    ApiErrorHandler.translations[ApiErrorCode.OWNER_STATUS_SAVE_INVALID_ID] = 'Status name must be at least one character and at most 100 characters.';
    ApiErrorHandler.translations[ApiErrorCode.REMINDER_EMPTY_TEXT_NOT_ALLOWED] = 'Reminders text must not be empty.';
    ApiErrorHandler.translations[ApiErrorCode.REMINDER_TEXT_TOO_LONG] = 'Reminders text must not be larger than 500 characters.';
    ApiErrorHandler.translations[ApiErrorCode.REMINDER_EMPTY_DUE_TIME_NOT_ALLOWED] = 'Reminders must not have an empty due time.';
    ApiErrorHandler.translations[ApiErrorCode.REMINDER_OWNER_WITH_GIVEN_ID_DOES_NOT_EXIST] = 'Owner with given ID does not exist. Either submit an existing owner ID or leave this input empty.';
    ApiErrorHandler.translations[ApiErrorCode.CANNOT_ADD_APPLICATION_MESSAGE_NO_SUCH_USER] = 'Unable to persist application message as the given recipient does not exist.';
    ApiErrorHandler.translations[ApiErrorCode.CANNOT_ADD_APPLICATION_MESSAGE_WITHOUT_TEXT] = 'Unable to persist application message as the message has not text.';
  }

  handle(error: any): ErrorObservable<any> {
    let result: ApiError = null;
    if (!error.error) {
      result = new ApiError(ApiErrorCode.OTHER, error.message);
    } else {
      const errorCode = error.error.code;
      if (errorCode) {
        const apiErrorCodeValue = ApiErrorCode[errorCode];
        const apiErrorCode = ApiErrorCode[apiErrorCodeValue];
        const translation = ApiErrorHandler.translations[apiErrorCodeValue];
        result = new ApiError(apiErrorCode, translation);
      } else {
        result = new ApiError(ApiErrorCode.OTHER, error.message);
      }
    }
    return ErrorObservable.create(result);
  }
}
