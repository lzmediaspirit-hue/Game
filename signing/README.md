# Android signing key

`jaderiver.keystore` signs both Jade River APKs (the clean build and the Max Test build). Every update must be
signed with this same key, or Android will refuse to install it over the old one.

- Type: PKCS12
- Alias: `jaderiver`
- Certificate SHA-256: `C1:A4:30:A6:31:A0:2B:2B:5F:CF:16:0A:19:97:B6:A2:74:80:3E:76:96:C5:24:A2:BF:E4:07:99:4C:BE:37:15`
- The store and key password are kept by the owner, not in this repository.

It sits outside the Godot project (`JadeRiver/`) so no export can ever pack it into an APK.

This repository is public: anyone can download this file. Before a Play Store release, either make the repository
private or create a new upload key and keep it out of the repository (Play App Signing lets the store hold the
app signing key itself).

Signing an exported APK (as the builds in `builds/` were):

```sh
java -jar uber-apk-signer.jar -a JadeRiver-unsigned.apk --ks signing/jaderiver.keystore \
  --ksAlias jaderiver --ksPass <password> --ksKeyPass <password> -o signed
```
