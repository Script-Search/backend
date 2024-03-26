package main

import (
	"fmt"
	"github.com/typesense/typesense-go/typesense"
)

var TypesenseClient *typesense.Client

func init() {
	TypesenseClient = typesense.NewClient(
	    typesense.WithServer(fmt.Sprintf("%s:%d", TypesenseHosts[0], TypesensePort)),
	    typesense.WithAPIKey(TypesenseAPIKey),
		typesense.WithConnectionTimeout(60))
}