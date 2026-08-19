package ee.metsad.register.mappers;

import ee.metsad.register.internalmodels.forestnotification.MetsAveTeatisDetailsResponse;
import ee.metsad.register.models.ForestNotificationModel;

public class ForestNotificationsResponseMapper {
    public ForestNotificationModel map(MetsAveTeatisDetailsResponse serviceResponse) {
        ForestNotificationModel notification = new ForestNotificationModel();
        notification.setNotificationId(serviceResponse.getId());
        notification.setNotificationNumber(parseLongSilent(serviceResponse.getTeatiseNr()));
        notification.setWorkCode(serviceResponse.getTooKood());
        notification.setState(serviceResponse.getOlek());
        notification.setDecision(serviceResponse.getOtsus());
        notification.setRegistrationDate(serviceResponse.getRegistreerimiseKp());
        notification.setConfirmationDate(serviceResponse.getOtsusKinnitatudKp());
        notification.setDamageCode(serviceResponse.getKahjustatudPuuliik());
        notification.setArea(serviceResponse.getPindala());
        notification.setAmountToBeCut(serviceResponse.getRaiutavMaht());
        notification.setCadastreSubPartCode(serviceResponse.getEraldiseNr());
        notification.setCadastreNo(serviceResponse.getKatastriNr());
        return notification;
    }

    private Long parseLongSilent(String l) {
        try {
            return Long.parseLong(l);
        } catch (Exception ignored) {
            return null;
        }
    }
}
