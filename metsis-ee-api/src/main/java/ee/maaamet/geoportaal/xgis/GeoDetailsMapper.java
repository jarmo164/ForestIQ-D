package ee.maaamet.geoportaal.xgis;

import java.util.Map;

public class GeoDetailsMapper {

    public GeoDetails map(Map<String, String> serviceResponse) {
        GeoDetails geoDetails = new GeoDetails();
        geoDetails.setMaakond(removeSS(serviceResponse.get("Maakond"), " maakond"));
        geoDetails.setVald(removeSS(serviceResponse.get("Omavalitsus"), " vald"));
        geoDetails.setKyla(serviceResponse.get("Asustusüksus"));
        geoDetails.setTunnus(serviceResponse.get("Tunnus"));
        geoDetails.setKinnistuNimi(serviceResponse.get("Lähiaadress"));
        geoDetails.setType(resolveType(
                IntendedPurpose.parse(serviceResponse.get("Sihtotstarve 1")),
                IntendedPurpose.parse(serviceResponse.get("Sihtotstarve 2")),
                IntendedPurpose.parse(serviceResponse.get("Sihtotstarve 3")))
        );
        geoDetails.setPindala(parseArea(serviceResponse.get("Pindala")));
        geoDetails.setHaritavMaa(parseArea(serviceResponse.get("Haritav maa")));
        geoDetails.setRohumaa(parseArea(serviceResponse.get("Rohumaa")));
        geoDetails.setMetsamaa(parseArea(serviceResponse.get("Metsamaa")));
        geoDetails.setOuemaa(parseArea(serviceResponse.get("Õuemaa")));
        geoDetails.setEhitisteAluneMaa(parseArea(serviceResponse.get("Ehitiste alune maa")));
        geoDetails.setMuuMaa(parseArea(serviceResponse.get("Muu maa")));
        geoDetails.setVeeAluneMaa(parseArea(serviceResponse.get("Veealune maa")));
        geoDetails.setRegistriosa(serviceResponse.get("Registriosa"));
        geoDetails.setKinnistupiirkondJaoskond(serviceResponse.get("Kinnistuspiirkond / jaoskond"));
        geoDetails.setMoodistamiseKuupaev(serviceResponse.get("Mõõdistamise kuupäev"));
        geoDetails.setMoodistaja(serviceResponse.get("Mõõdistaja"));
        geoDetails.setMoodistamisviis(serviceResponse.get("Mõõdistamisviis"));
        geoDetails.setHinnatsoon(removeHtml(removeNewlines(serviceResponse.get("Hinnatsoon"))));
        geoDetails.setViljakustsoon(removeHtml(removeNewlines(serviceResponse.get("Viljakustsoon"))));
        return geoDetails;
    }

    private Double parseArea(String original) {
        try {
            if (original == null) {
                return null;
            }
            String cleaned = original.trim().replace(" ha", "");
            return  Double.parseDouble(cleaned);
        } catch (Exception e) {
            // maybe its m2? if it is then convert to ha
            try {
                String[] split = original.trim().split(" ");
                if (split[1].startsWith("m")) {
                    return Double.parseDouble(split[0]) / 10000.0;
                }
                return 0.0;
            } catch (Exception ei) {
                return 0.0;
            }
        }
    }

    private String removeSS(String original, String ss) {
        return original == null ? null : original.replace(ss, "");
    }

    private String removeHtml(String content) {
        if (content == null) {
            content = "";
        }
        content = content.replace("<table><tr><td><a href=\"http://www.maaamet.ee/hv/389.pdf\" target=\"_blank\"><u><b>", "")
                .replace("</b></u></a></td><td>", "")
                .replace("</td></tr></table>", "")
                .replace("</td></tr><tr><td><a href=\"http://www.maaamet.ee/hv/389.pdf\" target=\"_blank\"><u><b>", "");
        return content;
    }

    private String removeNewlines(String text) {
        return text == null ? null : text.replaceAll("\r\n", " ").replaceAll("\n", " ");
    }
    
    private String resolveType(IntendedPurpose ip1, IntendedPurpose ip2, IntendedPurpose ip3) {
        String so1 = ip1 != null ? ip1.getName() : null;
        String so2 = ip2 != null ? ip2.getName() : null;
        String so3 = ip3 != null ? ip3.getName() : null;
        Integer so1ok = ip1 != null ? ip1.getPercentage() : null;
        Integer so2ok = ip2 != null ? ip2.getPercentage() : null;
        Integer so3ok = ip3 != null ? ip3.getPercentage() : null;
        if (isNullOrBlankString(so1)) {
            return null;
        }
        String result = so1;
        if (so1ok != null) {
            result += (" " + so1ok);
        }
        if (isNullOrBlankString((so2))) {
            return result;
        }
        result += ("; " + so2);
        if (so2ok != null) {
            result += (" " + so2ok);
        }
        if (isNullOrBlankString((so3))) {
            return result;
        }
        result += ("; " + so3);
        if (so3ok != null) {
            result += (" " + so3ok);
        }
        return result;
    }

    private static class IntendedPurpose {
        private final String name;
        private final Integer percentage;

        private IntendedPurpose(String name, Integer percentage) {
            this.name = name;
            this.percentage = percentage;
        }

        static IntendedPurpose parse(String soString) {
            try {
                if (soString != null) {
                    soString = soString.trim().replace("-", "");
                    if (soString.isEmpty()) {
                        soString = null;
                    }
                }
                if (soString == null) {
                    return new IntendedPurpose(null, null);
                }

                String[] split = soString.split(" ");
                int percentage = Integer.parseInt(split[split.length - 1].replace("%", "").trim());
                StringBuilder name = new StringBuilder();
                for (int i = 0; i < split.length - 1; i++) {
                    name.append(split[i]).append(" ");
                }
                return new IntendedPurpose(name.toString().trim(), percentage);
            } catch (Exception e) {
                return new IntendedPurpose(null, null);
            }
        }

        String getName() {
            return name;
        }

        Integer getPercentage() {
            return percentage;
        }
    }

    private boolean isNullOrBlankString(String given) {
        return given == null || given.trim().isEmpty();
    }
}
