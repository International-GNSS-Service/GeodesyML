### Updating antenna-receiver-codelists.xml

Prerequisites: Haskell Stack (https://docs.haskellstack.org/)

1) `wget https://igscb.jpl.nasa.gov/igscb/station/general/rcvr_ant.tab`
2) Bump `versionNumber` and `versionDate` in `antenna-receiver-codelists.tpl`
3) `./generate-antenna-receiver-codelists.sh`
4) commit modified files

TODO: Only receiver and antenna type code lists are currently in use.
