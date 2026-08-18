# ChangeRequestResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**document_id** | **string** |  | [default to undefined]
**requester_id** | **string** |  | [default to undefined]
**title** | **string** |  | [default to undefined]
**description** | **string** |  | [default to undefined]
**status** | [**ChangeRequestStatus**](ChangeRequestStatus.md) |  | [default to undefined]
**assignee_id** | **string** |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]
**updated_at** | **string** |  | [default to undefined]
**proposals** | [**Array&lt;ChangeProposalResponse&gt;**](ChangeProposalResponse.md) |  | [optional] [default to undefined]
**comments** | [**Array&lt;ChangeCommentResponse&gt;**](ChangeCommentResponse.md) |  | [optional] [default to undefined]

## Example

```typescript
import { ChangeRequestResponse } from './api';

const instance: ChangeRequestResponse = {
    id,
    document_id,
    requester_id,
    title,
    description,
    status,
    assignee_id,
    created_at,
    updated_at,
    proposals,
    comments,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
