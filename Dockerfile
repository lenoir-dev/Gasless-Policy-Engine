FROM golang:1.27.2-bookworm@sha256:5cf287a799e6b94384bad13d16b14904c531f51ba65792237e122ce42b392f61 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -buildvcs=false -ldflags='-s -w' -o /gasless ./cmd/gasless

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /gasless /gasless
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/gasless"]
