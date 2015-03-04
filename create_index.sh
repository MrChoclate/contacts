curl -XPUT "127.0.0.1:9200/contacts" -d '{
    "mappings": {
        "event" : {
            "properties": {
                "name": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "location": {
                    "type": "string",
                    "index": "not_analyzed"
                }
            }
        },
        "contact": {
            "_parent": {
                "type": "event"
            },
            "properties": {
                "last_name": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "first_name": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "gender": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "postal_code": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "street": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "town": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "country": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "mail": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "mail2": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "phone": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "degree": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "studies": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "comment": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "eisti": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "date": {
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss.SSSSSS"
                }
            }
        }
    }
}
'