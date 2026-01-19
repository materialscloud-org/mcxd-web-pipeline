# Pipeline scripts to generate the MC3D and MC2D data for the web

To generate the web metadata:

- Set up the AiiDA profiles (see https://github.com/materialscloud-org/aiida-server)
- Set up a MongoDB.
- Update the `config.yaml` to reflect your setup (MongoDB URI, AiiDA profile names, ...)
- Install this package, and see
  ```
  > mcxd-web-pipeline --help
  ```

To deploy any updated data:

- dump the mongodb collections & upload to S3 (via CLI);
- And the Materials Cloud deployment (ArgoCD job, needs a re-run) will import any updated mongoDB collections from S3.
