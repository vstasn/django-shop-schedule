# Django shop schedule

[![CircleCI](https://circleci.com/gh/vstasn/django-shop-schedule.svg?style=svg)](https://circleci.com/gh/vstasn/django-shop-schedule)

## Request & Response Examples

### API Resources

  - [POST /api/user/register/](#user-register)
  - [POST /api/user/login/](#user-login)
  - [POST /api/shop/](#create-shop)
  - [POST /api/shop/[id]/schedule](#get-schedule)
  - [POST /api/shop/[id]/is_working](#check-is-working)
  - [POST /api/shop/[id]/update_schedule](#update-schedule)
  - [POST /api/shop/[id]/close](#close-shop)

### POST /api/user/register/

Register new user

### POST /api/user/login/

Login and get AuthToken

### POST /api/shop/

Create new shop with owner=request.user

### POST /api/shop/[id]/schedule

Get shop schedule

Example: http://example.com/api/shop/[id]/schedule

### POST /api/shop/[id]/is_working

Check if shop is working now

Example: http://example.com/api/shop/[id]/is_working

### POST /api/shop/[id]/update_schedule

Update shop schedule

Example: http://example.com/api/shop/[id]/update_schedule

### POST /api/shop/[id]/close

Close shop (can set a few days)

Example: http://example.com/api/shop/[id]/close