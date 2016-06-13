
from setuptools import setup, find_packages


setup(
    name='CSCW Voucher Application',
    version='0.0.1',
    description='Digital Voucher Application as an alternative for sodexo like vouchers',
    long_description=__doc__,
    url='https://github.com/lakxraju/CSCW_Voucher_Application/',
    author='Lakshminarayanan Rajendran',
    author_email='lakxraju@gmail.com',
    zip_safe=False,


    packages=find_packages(),

    install_requires=[
        "BigchainDB==0.4.0",
        "flask==0.10.1",
        "flask-cors==2.1.2",
        "flask_restful"
    ]

)
