#!/bin/bash
curl -Ls "https://raw.githubusercontent.com/LamaAni/zbash-commons/master/install?ts_$(date +%s)=read" | bash || exit $?
source zlib_commons || exit $?

log:info "zlib commons installed."
