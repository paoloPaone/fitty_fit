SERVICE := fittyfit
DESTDIR ?= dist_root
SERVICEDIR ?= /srv/$(SERVICE)

.PHONY: build install

build:
	echo nothing to build

install: build
	mkdir -p $(DESTDIR)$(SERVICEDIR)
	cp -r src/fittyfit $(DESTDIR)$(SERVICEDIR)
	cp -r src/docker-compose.yml $(DESTDIR)$(SERVICEDIR)

clean:
	rm -rf $(DESTDIR)$(SERVICEDIR)/data
