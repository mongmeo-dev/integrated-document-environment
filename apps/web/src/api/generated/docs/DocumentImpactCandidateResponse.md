# DocumentImpactCandidateResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**source_document_id** | **string** |  | [default to undefined]
**source_location** | **string** |  | [default to undefined]
**target_document_id** | **string** |  | [default to undefined]
**target_location** | **string** |  | [default to undefined]
**reason** | **string** |  | [default to undefined]
**proposed_modification** | **string** |  | [default to undefined]
**status** | [**CandidateStatus**](CandidateStatus.md) |  | [default to undefined]
**modification_required** | **boolean** |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]
**decided_at** | **string** |  | [default to undefined]
**decided_by_id** | **string** |  | [default to undefined]
**modification_decided_at** | **string** |  | [default to undefined]
**modification_decided_by_id** | **string** |  | [default to undefined]

## Example

```typescript
import { DocumentImpactCandidateResponse } from './api';

const instance: DocumentImpactCandidateResponse = {
    id,
    source_document_id,
    source_location,
    target_document_id,
    target_location,
    reason,
    proposed_modification,
    status,
    modification_required,
    created_at,
    decided_at,
    decided_by_id,
    modification_decided_at,
    modification_decided_by_id,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
