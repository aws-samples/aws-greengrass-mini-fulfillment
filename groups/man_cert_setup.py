#!/usr/bin/env python

from OpenSSL import crypto
import argparse


def create_group_cert(cli):
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)  # generate RSA key-pair

    cert = crypto.X509()
    cert.get_subject().countryName = "US"
    cert.get_subject().stateOrProvinceName = "CA"
    cert.get_subject().organizationName = "mini-fulfillment"
    cert.get_subject().organizationalUnitName = "demo"
    cert.get_subject().commonName = "mini-fulfillment"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(5 * 365 * 24 * 60 * 60)  # 5 year expiry date
    cert.set_issuer(cert.get_subject())  # self-sign this certificate
    cert.set_pubkey(k)
    san_list = ["IP:{0}".format(cli.ip_address)]
    extension_list = [
        crypto.X509Extension(type_name=b"basicConstraints",
                             critical=False, value=b"CA:false"),
        crypto.X509Extension(type_name=b"subjectAltName",
                             critical=True, value=", ".join(san_list)),
        # crypto.X509Extension(type_name=b"subjectKeyIdentifier",
        #                      critical=True, value=b"hash")
    ]
    cert.add_extensions(extension_list)
    cert.sign(k, 'sha256')

    prefix = str(cli.out_dir) + '/' + cli.group_name

    open("{0}-server.crt".format(prefix), 'wt').write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    open("{0}-server-private.key".format(prefix), 'wt').write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey=k))
    open("{0}-server-public.key".format(prefix), 'wt').write(
        crypto.dump_publickey(crypto.FILETYPE_PEM, pkey=k))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Greengrass Group Certificate provisioning',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers()

    group_names = [
        'inv_arm',
        'master',
        'sort_arm'
    ]
    create_parser = subparsers.add_parser(
        'create',
        description='Create CA and Certificate for the Demo')
    create_parser.set_defaults(func=create_group_cert)
    create_parser.add_argument('group_name', choices=group_names,
                               help="The group certificate to create.")
    create_parser.add_argument('ip_address',
                               help="The IP address to use in the certificate.")
    create_parser.add_argument('--out-dir', dest='out_dir', default='.',
                               help="The output directory for the group certs.")
    args = parser.parse_args()
    # if args.debug:
    #     logging.basicConfig(
    #         format='%(asctime)s|%(name)-8s|%(levelname)s: %(message)s',
    #         level=logging.DEBUG)

    args.func(args)
