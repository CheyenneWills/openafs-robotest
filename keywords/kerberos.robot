*** Setting ***
Library    OperatingSystem
Variables  variables/${ENV_DIST}/paths.py


*** Keywords ***
set kerberos realm
    [arguments]    ${realm}
    file should not exist    ${AFS_SERVER_ETC_DIR}krb.conf
    create file    /tmp/krb.conf    ${realm}
    sudo    cp /tmp/krb.conf ${AFS_SERVER_ETC_DIR}/krb.conf
    run    rm /tmp/krb.conf

should not have kerberos tickets
    ${rc}    ${output}    run and return rc and output    klist -5
    log    ${output}
    should be equal as integers  ${rc}  1

Should have kerberos tickets
    ${rc}    ${output}    run and return rc and output    klist -5
    log    ${output}
    should be equal as integers  ${rc}  0
