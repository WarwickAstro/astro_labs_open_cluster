import argparse as ap

def arg_parse():
    p = ap.ArgumentParser('Bump open_clusters version number')
    p.add_argument('version',
                   type=str,
                   help='New version number')
    return p.parse_args()

if __name__ == "__main__":
    args = arg_parse()
    with open('open_clusters_version.py', 'w') as ver:
        ver.write(f"VERSION='{args.version}'")
