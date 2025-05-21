# MongoDB for Umbrel

A ready-to-use MongoDB database server for your Umbrel. This app provides a clean MongoDB instance that can be used by other apps in your Umbrel ecosystem.

## Features

- MongoDB 7.0
- Persistent data storage
- Pre-configured with secure defaults
- Ready to use in your app development

## Connection Details

- **Username**: `umbrel`
- **Password**: `umbrel`
- **Port**: `27017`
- **Host**: `bitsperity-mongodb` (within Umbrel network)

## How to Connect

### Connection URI
Other apps on your Umbrel can connect using:

```
mongodb://umbrel:umbrel@bitsperity-mongodb:27017/
```

Note: When connecting from within the Docker network, use port 27017. The 27017 port is also used for connections from outside the Docker network.

### Creating a Database

To create and use a specific database:

```
mongodb://umbrel:umbrel@bitsperity-mongodb:27017/your_database_name
```

## Data Persistence

All data is stored in a Docker volume and persists across app restarts and updates.

## Security Notice

This MongoDB instance is only accessible within the Umbrel Docker network by default. The external port 27017 can be used for connections from your local network.

## Support

If you encounter any issues or have questions, please open an issue at:
[https://github.com/bitsperity/bitsperity_apps/issues](https://github.com/bitsperity/bitsperity_apps/issues)

## Developed by

[Bitsperity](https://bitsperity.dev) 