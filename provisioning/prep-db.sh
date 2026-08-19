psql -h metsis.csm17oojwg6o.eu-north-1.rds.amazonaws.com -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
  CREATE USER $1 WITH PASSWORD '$2';
  GRANT $1 TO postgres;
  CREATE DATABASE $1 WITH ENCODING='UTF8' OWNER=$1;
EOSQL
