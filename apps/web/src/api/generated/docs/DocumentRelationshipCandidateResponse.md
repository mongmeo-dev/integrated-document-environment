# DocumentRelationshipCandidateResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**source_document_id** | **string** |  | [default to undefined]
**source_location** | **string** |  | [default to undefined]
**target_document_id** | **string** |  | [default to undefined]
**target_location** | **string** |  | [default to undefined]
**relationship_type** | [**RelationshipType**](RelationshipType.md) |  | [default to undefined]
**reason** | **string** |  | [default to undefined]
**status** | [**CandidateStatus**](CandidateStatus.md) |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]
**decided_at** | **string** |  | [default to undefined]
**decided_by_id** | **string** |  | [default to undefined]
**analysis_run_id** | **string** |  | [default to undefined]

## Example

```typescript
import { DocumentRelationshipCandidateResponse } from './api';

const instance: DocumentRelationshipCandidateResponse = {
    id,
    source_document_id,
    source_location,
    target_document_id,
    target_location,
    relationship_type,
    reason,
    status,
    created_at,
    decided_at,
    decided_by_id,
    analysis_run_id,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
