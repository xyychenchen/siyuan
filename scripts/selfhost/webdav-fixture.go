// SiYuan - https://github.com/siyuan-note/siyuan
// Copyright (c) 2020-present, b3log.org
// SPDX-License-Identifier: AGPL-3.0-or-later

package main

import (
	"golang.org/x/net/webdav"
	"net/http"
	"os"
)

func main() {
	h := &webdav.Handler{FileSystem: webdav.Dir(os.Args[1]), LockSystem: webdav.NewMemLS()}
	http.ListenAndServe("127.0.0.1:16807", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		u, p, ok := r.BasicAuth()
		if !ok || u != "test" || p != "fixture-only" {
			w.Header().Set("WWW-Authenticate", `Basic realm="test"`)
			w.WriteHeader(401)
			return
		}
		h.ServeHTTP(w, r)
	}))
}
