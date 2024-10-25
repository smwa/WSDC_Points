#!/bin/env bash
bundle install
JEKYLL_ENV=development bundle exec jekyll serve -w --force_polling
