package ee.metsis.personsdump;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class PersonsDumpService {

    private final PersonsDumpDao personsDumpDao;
    private List<PersonsDumpEntry> loaded;

    public PersonsDumpService(PersonsDumpDao personsDumpDao) {
        this.personsDumpDao = personsDumpDao;
    }

    public List<PersonsDumpEntry> searchEntries(PersonsDumpCriteria criteria) {
        if (loaded == null) {
            loaded = personsDumpDao.findAll();
        }
        Stream<PersonsDumpEntry> loadedStream = loaded.stream();
        if (criteria.getName().isPresent()) {
            String name = criteria.getName().get().toLowerCase();
            loadedStream =
                    loadedStream.filter(e ->
                            Optional.ofNullable(e.getName())
                                    .map(String::toLowerCase)
                                    .map(it -> it.contains(name))
                                    .orElse(false)
                    );
        }
        if (criteria.getAddress().isPresent()) {
            String address = criteria.getAddress().get().toLowerCase();
            loadedStream =
                    loadedStream.filter(e ->
                            Optional.ofNullable(e.getAddress())
                                    .map(String::toLowerCase)
                                    .map(it -> it.contains(address))
                                    .orElse(false)
                    );
        }
        if (criteria.getCode().isPresent()) {
            String code = criteria.getCode().get().toLowerCase();
            loadedStream =
                    loadedStream.filter(e ->
                            Optional.ofNullable(e.getCode())
                                    .map(String::toLowerCase)
                                    .map(it -> it.contains(code))
                                    .orElse(false)
                    );
        }
        if (criteria.getPhone().isPresent()) {
            String phone = criteria.getPhone().get().toLowerCase();
            loadedStream =
                    loadedStream.filter(e ->
                            Optional.ofNullable(e.getPhone())
                                    .map(String::toLowerCase)
                                    .map(it -> it.contains(phone))
                                    .orElse(false)
                    );
        }
        if (criteria.getSource().isPresent()) {
            String source = criteria.getSource().get().toLowerCase();
            loadedStream =
                    loadedStream.filter(e ->
                            Optional.ofNullable(e.getSource())
                                    .map(String::toLowerCase)
                                    .map(it -> it.contains(source))
                                    .orElse(false)
                    );
        }
        if (criteria.getName().isPresent()) {
            String proposedNameLower = criteria.getName().get().toLowerCase();
            loadedStream = loadedStream.sorted((o1, o2) -> {
                String o1n = o1.getName().toLowerCase();
                String o2n = o2.getName().toLowerCase();
                boolean o1nExactMatch = o1n.equals(proposedNameLower)
                        || o1n.startsWith(proposedNameLower + " ")
                        || o1n.endsWith(" " + proposedNameLower)
                        || o1n.contains(" " + proposedNameLower + " ");
                boolean o2nExactMatch = o2n.equals(proposedNameLower)
                        || o2n.startsWith(proposedNameLower + " ")
                        || o2n.endsWith(" " + proposedNameLower)
                        || o2n.contains(" " + proposedNameLower + " ");
                if (o1nExactMatch && !o2nExactMatch) {
                    return -1;
                }
                if (o2nExactMatch && !o1nExactMatch) {
                    return 1;
                }

                return 0;
            });
        }

        return loadedStream.limit(1000).collect(Collectors.toList());
    }

    public void addEntry(NewPersonsDumpEntry entry) {
        personsDumpDao.addEntry(entry);
    }

    public void deleteEntry(Long id) {
        personsDumpDao.deleteEntry(id);
    }
}
