# DocumentEvidenceLinkResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**document_id** | **string** |  | [default to undefined]
**evidence_id** | **string** |  | [default to undefined]
**status** | [**EvidenceLinkStatus**](EvidenceLinkStatus.md) |  | [default to undefined]
**freshness** | [**EvidenceFreshness**](EvidenceFreshness.md) |  | [default to undefined]
**reason** | **string** |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]
**decided_by_id** | **string** |  | [default to undefined]
**decided_at** | **string** |  | [default to undefined]
**reviewed_by_id** | **string** |  | [default to undefined]
**reviewed_at** | **string** |  | [default to undefined]
**analysis_run_id** | **string** |  | [default to undefined]

## Example

```typescript
import { DocumentEvidenceLinkResponse } from './api';

const instance: DocumentEvidenceLinkResponse = {
    id,
    document_id,
    evidence_id,
    status,
    freshness,
    reason,
    created_at,
    decided_by_id,
    decided_at,
    reviewed_by_id,
    reviewed_at,
    analysis_run_id,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
