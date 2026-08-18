# DocumentRelationshipCandidateCreate


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source_document_id** | **string** |  | [default to undefined]
**source_location** | **string** |  | [default to undefined]
**target_document_id** | **string** |  | [default to undefined]
**target_location** | **string** |  | [default to undefined]
**relationship_type** | [**RelationshipType**](RelationshipType.md) |  | [default to undefined]
**reason** | **string** |  | [default to undefined]

## Example

```typescript
import { DocumentRelationshipCandidateCreate } from './api';

const instance: DocumentRelationshipCandidateCreate = {
    source_document_id,
    source_location,
    target_document_id,
    target_location,
    relationship_type,
    reason,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
