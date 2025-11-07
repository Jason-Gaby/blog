# Use an official Python runtime as parent image
FROM rockylinux/python:3.13

# Add user that will be used in the container.
RUN useradd wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000
    DJANGO_SETTINGS_MODULE=mysite.settings.production

# Install system packages required by Wagtail and Django.
RUN dnf update -y && dnf install -y \
    gcc \
    mariadb-devel \
    postgresql-devel \
    libjpeg-turbo-devel \
    zlib-devel \
    libwebp-devel \
 && dnf clean all \
 && rm -rf /var/cache/dnf

# Install the application server.
RUN pip install "gunicorn==20.0.4"

# Install the project requirements.
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Set this directory to be owned by the "wagtail" user. This Wagtail project
# uses SQLite, the folder needs to be owned by the user that
# will be writing to the database file.
RUN chown wagtail:wagtail /app

# Copy the source code of the project into the container.
COPY --chown=wagtail:wagtail . .

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Runtime command that executes when "docker run" is called, it does the
# following:
#   1. Start the application server, WSGI, and reverse proxy
CMD systemctl enable --now gunicorn.socket
CMD systemctl enable --now gunicorn.service
CMD systemctl enable --now nginx
CMD sleep 1
CMD systemctl restart gunicorn.socket
CMD systemctl restart gunicorn.service
CMD systemctl restart nginx
