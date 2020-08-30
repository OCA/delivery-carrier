## To install OSRM with docker-compose :


* On the osrm/Dockerfile with one `OSRM_REGION` defined eg you can replace by monaco-latest finded in http://download.geofabrik.de/europe/monaco.html:
```
FROM osrm/osrm-backend:latest


RUN mkdir osrm && cd osrm && \
    apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/* && \
    wget http://download.geofabrik.de/europe/OSRM_REGION.osm.pbf -O osrm-region-latest.osm.pbf && \
    osrm-extract -p /opt/car.lua osrm-region-latest.osm.pbf && \
    osrm-contract osrm-region-latest.osrm
CMD  ["osrm-routed", "osrm/osrm-region-latest.osrm"]
```

* On the odoo/Dockerfile add thing like:
```
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
        parallel libmagic1 libgdal-dev python3-tk \
        # if you need some dev packages for python packages, you need to clean them afterwards
        python3-dev build-essential \
        && export CPLUS_INCLUDE_PATH=/usr/include/gdal \
        && export C_INCLUDE_PATH=/usr/include/gdal \
        && cd /odoo \
        && find . -maxdepth 1 -name "*requirements.txt" ! -name src_requirements.txt ! -name base_requirements.txt | xargs -I{} pip install -r {} \
        # cleaning of dev packages
        && apt-get remove -y build-essential python3-dev \
        # && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false -o APT::AutoRemove::SuggestsImportant=false \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
```


* On the docker-compose.yml add the osrm conteneur

```
osrm:
  build: ./osrm/
  ports:
	- 5000:5000
```

and `odoo` service should depends off `osrm`

* In you requirement:

```
## dev or_tools
ortools
gdal==2.2
pynominatim
osrm
matplotlib==2.2.4
routing-ortools-osrm==1.0.0
```
