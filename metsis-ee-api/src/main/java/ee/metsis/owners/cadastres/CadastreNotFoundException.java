package ee.metsis.owners.cadastres;

import ee.finenet.fineframe.exceptions.ResourceNotFoundException;

public class CadastreNotFoundException extends ResourceNotFoundException {
    public CadastreNotFoundException() {
        super("CADASTRE_NOT_FOUND");
    }
}
