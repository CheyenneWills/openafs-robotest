# Copyright (c) 2015 Sine Nomine Associates
# Copyright (c) 2001 Kungliga Tekniska Högskolan
# See LICENSE

*** Settings ***
Documentation     Volume salvaging tests
Resource          openafs.robot

*** Test Cases ***
Restore Volume with a Bad Uniquifier in it, salvage, check
    [Tags]  todo  arla  #(baduniq)
    TODO