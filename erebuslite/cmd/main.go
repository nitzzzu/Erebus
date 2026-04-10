// Package main is the entry point for ErebusLite — a lightweight Go
// reimplementation of Erebus using the Eino AI framework.
package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/nitzzzu/Erebus/erebuslite/internal/config"
	"github.com/nitzzzu/Erebus/erebuslite/internal/gateway"
)

func main() {
	cfg := config.Load()

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	srv, err := gateway.New(cfg)
	if err != nil {
		log.Fatalf("failed to create gateway: %v", err)
	}

	addr := fmt.Sprintf("%s:%d", cfg.APIHost, cfg.APIPort)
	log.Printf("ErebusLite gateway starting on %s", addr)

	if err := srv.Run(ctx, addr); err != nil {
		log.Fatalf("gateway error: %v", err)
	}
}
