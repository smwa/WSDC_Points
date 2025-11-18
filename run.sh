#!/bin/env bash
bundle3.3 install
JEKYLL_ENV=development bundle3.3 exec jekyll serve -w --force_polling --incremental
