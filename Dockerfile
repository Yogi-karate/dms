FROM tramm/odoo_dms
MAINTAINER ram tangirala<ram.tangirala@gmail.com>

# Generate locale C.UTF-8 for postgres and general locale data
ENV LANG C.UTF-8



# Install Odoo
ENV ODOO_VERSION 12.0
ENV ODOO_RELEASE 20181008

# Copy entrypoint script and Odoo configuration file

COPY ./modules/ /odoo/addons/
COPY ./odoo.conf /etc/odoo/


