source .env

curl -X POST http://127.0.0.1:8000/api-property/front-property-listing/ \
  -H "Authorization: Token $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"site_id":"3","page_size":5,"page":1}'
