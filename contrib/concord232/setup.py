from setuptools import setup

setup(name='concord232',
      version='0.0.1',
      description='Provides Home Assistant interface for concordd replicating the current concord232 integration',
      author='Jon Vadney',
      author_email='jon.vadney@gmail.com',
      url='https://github.com/jonvadney/concordd',
      packages=['concord232'],
      install_requires=['requests', 'prettytable', 'flask', 'dbus'],
      scripts=['concord232_server', 'concord232_client']
  )
