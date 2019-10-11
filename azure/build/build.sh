#! /usr/bin/env bash
rm -f ../built/scripts.tar.gz
#dos2unix ../scripts/*
# Pack up scripts into an archive
tar cvz ../scripts/* > ../built/scripts.tar.gz