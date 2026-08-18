# HistoryEvent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**type** | **string** |  | [default to undefined]
**document_id** | **string** |  | [default to undefined]
**actor_id** | **string** |  | [default to undefined]
**occurred_at** | **string** |  | [default to undefined]
**reason** | **string** |  | [default to undefined]
**before** | **{ [key: string]: any; }** |  | [default to undefined]
**after** | **{ [key: string]: any; }** |  | [default to undefined]
**source_id** | **string** |  | [default to undefined]

## Example

```typescript
import { HistoryEvent } from './api';

const instance: HistoryEvent = {
    id,
    type,
    document_id,
    actor_id,
    occurred_at,
    reason,
    before,
    after,
    source_id,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
