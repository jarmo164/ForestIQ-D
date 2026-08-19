FROM nginx

ENV TZ="Europe/Tallinn"
RUN date

COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
COPY ssh/fullchain.pem /etc/nginx/ssl/server.pem
COPY ssh/privkey.pem /etc/nginx/ssl/server.key
