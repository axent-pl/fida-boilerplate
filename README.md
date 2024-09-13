# FIDA boilerplate
A boilerplate application stack for company to conform to FIDA regulation

## Keycloak configuration

* realm: fida
* clients:
    * fisp-acme:Mn9IfxIoZDL2eCQYigVgt8wF0zaQMzeN
    * fisp-umbrella:HoaVH4v1RtU1afL73gnm7bC50DPqUyEv
* users:
    * jane-bar-com:jane-bar-com-password
    * john-foo-com:john-foo-com-password


### Flow

http://localhost:2380/auth/realms/fida/protocol/openid-connect/auth?client_id=fisp-acme&scope=fida-deposit&response_type=code

http://localhost:2380/auth/?session_state=3f0186f3-61bf-4bfa-8a74-35c23ac5c41e&iss=http%3A%2F%2Flocalhost%3A2380%2Fauth%2Frealms%2Ffida&code=0f464b0c-d076-48d6-9d38-513916d1e660.3f0186f3-61bf-4bfa-8a74-35c23ac5c41e.d9fb35fb-5daa-419c-81f1-dae4743db70e/