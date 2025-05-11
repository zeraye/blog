+++
title = "Smaller and more secure Docker images for Golang"
date = 2025-05-11
+++

### Preface

In this article I want to show you, how to build smaller and more secure Docker images for Golang. I won't only show how to do this, but more importantly why. I want to emphasize one obvious and crucial thing. This article **won't make your images secure**. Security isn't one time thing. It's your responsibility to handle vunerabilities inside code and it's dependenciecs. It will help by reducing potentntial vunerabilities in the base image and applying some best practices for building Docker image for Golang.

### Code

I used `github.com/google/uuid` library to have some dependency. We will need it later.

`main.go`

```go
package main

import (
	"fmt"

	"github.com/google/uuid"
)

func main() {
	fmt.Println(uuid.NewString())
}
```

`go.mod`

```
module github.com/zeraye/tiny-go-docker

go 1.24.3

require github.com/google/uuid v1.6.0
```

`go.sum`

```
github.com/google/uuid v1.6.0 h1:NIvaJDMOsjHA8n1jAhLSgzrAzy1Hgr+hNrb57e+94F0=
github.com/google/uuid v1.6.0/go.mod h1:TIyPZe4MgqvfeYDBFedMoGGpEw/LqOeaOT+nhxU+yHo=
```

### Step 1

When you build your first Golang image, you will end up with something like this:

```docker
FROM golang:1.24.3-alpine3.21

WORKDIR /app

COPY . .

RUN go mod download

RUN go build -o /main .

CMD ["/main"]
```

It weights 316MB, that's a lot. There are also a lot of things we can improve in terms of security and image size. Let's get to work:

#### 1. Verify downloaded dependencies.

You can verify that the dependencies of the current module, which are stored in a local downloaded source cache, have not been modified since being downloaded:

```docker
RUN go mod download && go mod verify
```

Let's assume someone tampers source of `github.com/google/uuid v1.6.0`. Next time you try to download this package, verification process will return non-zero exit code with something like this:

```
github.com/google/uuid v1.6.0: dir has been modified
```

#### 2. First download dependencies then build the project.

You don't want to download dependencies every time you change something in the source code. Let's download dependencies and then build project. Now after you change some code, layer with downloading dependencies would be cached:

```docker
COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN go build -o /main .
```

_Note: `go build` will download dependecies by itself, so example from the beginning where `go mod download` is directly over `go build` would work without `RUN go mod download` line._

#### 3. Run as non-root user.

This is well known security practice. I don't have anything more to add here. See [Docker best practices about USER](https://docs.docker.com/build/building/best-practices/#user) or search it.

```docker
FROM golang:1.24.3-alpine3.21

# rest of the Dockerfile...

USER nobody:nobody

CMD ["/main"]
```

_Note: User and group nobody is build in alpine image._

### Step 2

Let's apply all suggestions from step 1 and see what we got:

```docker
FROM golang:1.24.3-alpine3.21

WORKDIR /app

COPY go.mod go.sum ./

RUN go mod download && go mod verify

COPY . .

RUN go build -o /main .

USER nobody:nobody

CMD ["/main"]
```

It still weights 316MB, but it's much more secure and bulding is faster, because we better handle dependencies caching. Now let's get image size as tiny as we can:

#### 1. Use `scratch` image.

We can utilize [Docker `scratch` image](https://docs.docker.com/build/building/base-images/#create-a-minimal-base-image-using-scratch). It's quite light, because it weights 0 bytes. Let's build our binary using `golang:1.24.3-alpine3.21`, and then run binary in the `scratch` image:

```docker
FROM golang:1.24.3-alpine3.21 AS build

WORKDIR /app

COPY go.mod go.sum ./

RUN go mod download && go mod verify

COPY . .

RUN go build -o /main .

FROM scratch

COPY --from=build /main /main

USER nobody:nobody

CMD ["/main"]
```

After we build it we get:

```
docker: Error response from daemon: unable to find user nobody: no matching entries in passwd file
```

Oh, `scratch` doesn't have `nobody` user built-in (or any user). We neeed to copy `/etc/passwd` and `/etc/group` from our `build` image:

```docker
FROM golang:1.24.3-alpine3.21 AS build

# same as above...

FROM scratch

COPY --from=build /etc/passwd /etc/passwd
COPY --from=build /etc/group /etc/group
COPY --from=build /main /main

USER nobody:nobody

CMD ["/main"]
```

It works, and our final image has 2.47MB. Is that it? Can we grab a drink and chill now? Not really. Our Docker image is missing 3 key components: CA certificates, timezones and build with static binary. Let's work on examples:

```go
package main

import (
	"log/slog"
	"net/http"
)

func main() {
	resp, err := http.Get("https://example.com")
	if err != nil {
		slog.Error("failed to make request", slog.Any("error", err))
		return
	}
	defer resp.Body.Close()

	slog.Info("response from request", slog.String("status", resp.Status))
}
```

After we build and run we get:

```
2025/05/11 12:37:25 ERROR failed to make request error="Get \"https://example.com\": tls: failed to verify certificate: x509: certificate signed by unknown authority"
```

We need CA certificates to make `https` requests. We can easily add them, by just adding one line:

```docker
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
```

Now let's take a look at timezones:

```go
package main

import (
	"log/slog"
	"time"
)

func main() {
	loc, err := time.LoadLocation("Europe/Warsaw")
	if err != nil {
		slog.Error("failed to load timezone:", slog.Any("error", err))
		return
	}

	now := time.Now().In(loc)
	slog.Info("current time in Europe/Warsaw", slog.String("time", now.Format(time.RFC3339)))
}
```

After we run it, we get:

```
2025/05/11 12:43:27 ERROR failed to load timezone: error="unknown time zone Europe/Warsaw"
```

We are missing timezones! Let's add them to our `build` image and then copy to `scratch` image:

```docker
FROM golang:1.24.3-alpine3.21 AS build

RUN apk add --no-cache tzdata

# some other stuff...

FROM scratch

COPY --from=build /usr/share/zoneinfo /usr/share/zoneinfo

# rest of the Dockerfile...
```

The last thing is static binary. Golang programs are statically linked by default, but there is exception. When we use `cgo` (C bindings), the binary becomes dynamically linked. We can disable it by setting environmental variable `CGO_ENABLED` to 0:

```docker
RUN CGO_ENABLED=0 go build -o /main .
```

#### 2. Optimize build flags.

We can reduce binary size by stripping debug information `-ldflags="-s -w"` and removing local file system paths from the complied binary `-trimpath`, so we end up with:

```docker
RUN go build ldflags="-s -w" -trimpath -o /main .
```

### Step 3

After we update our Dockerfile from step 2 with suggestions we get:

```docker
FROM golang:1.24.3-alpine3.21 AS build

RUN apk add --no-cache tzdata

WORKDIR /app

COPY go.sum go.mod ./

RUN go mod download && go mod verify

COPY . .

RUN CGO_ENABLED=0 go build -ldflags="-s -w" -trimpath -o /main .

FROM scratch

COPY --from=build /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build /etc/passwd /etc/passwd
COPY --from=build /etc/group /etc/group
COPY --from=build /main /main

USER nobody:nobody

CMD ["/main"]
```

Our Docker image for Golang weights only 2.48MB. We reduced it from 316MB (99.2%). Great job!

### Afterword

I intentionaly didn't include pinning base image version to digest, because it may introduce new vunerabilities instead of reducing it. It's up to you. Learn more about [pin base image versions here](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions). If you spot any mistake or want to improve this blog post contact me at jakub@rudnik.io. Source code is available [here](https://github.com/zeraye/tiny-go-docker).
