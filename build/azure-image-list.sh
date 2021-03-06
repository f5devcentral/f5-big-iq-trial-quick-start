#!/usr/bin/env bash

az login
az vm image list --all --publisher f5-networks --offer f5-big-iq
