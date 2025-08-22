

The follow example illustrates loading IP products and chips for
audit via primarily driven by python and CSV files.  Python is
used to facilitate the handling of custom python data that is 
assigned to labels attached to products, chips, etc.

The scripts create a sample company and load IP products for use
to associate to a chip for validation.  The CSV file for IP products
include the product metadata and path to load from.   The CSV
file for the chip links dependent IP products for the chip.  The
IP products are linked to the chip by the IPID of the IP product.

Step 0. Authenticate with proper permissions.

% ipg auth login ipgrid_admin@localhost:4000 --password ipgrid_pwd

Step 1. Create the company we will use to associate our sample IP 
products

% ipg auth company create --company mystic --legal-name "Mystic, Co" \
        --email info@mystic.com --url "http://www.mystic.com"

Step 2. Load the IP products using mystic.csv CSV file, add 
labels with extra metadata for linking purposes.

% python3 load_ip_products.py mystic.csv

Step 3. Load the chip, link associated IP products using another
CSV file

% python3 load_chip.py sierra 82443 82443.csv         

