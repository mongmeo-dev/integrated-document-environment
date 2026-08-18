# DocumentResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**original_file** | [**OriginalFileResponse**](OriginalFileResponse.md) |  | [default to undefined]
**status** | [**DocumentStatus**](DocumentStatus.md) |  | [default to undefined]
**input_kind** | [**InputKind**](InputKind.md) |  | [default to undefined]
**capabilities** | [**DocumentCapabilities**](DocumentCapabilities.md) |  | [default to undefined]
**rejection** | [**DocumentRejection**](DocumentRejection.md) |  | [default to undefined]
**creator** | [**DocumentCreator**](DocumentCreator.md) |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]

## Example

```typescript
import { DocumentResponse } from './api';

const instance: DocumentResponse = {
    id,
    original_file,
    status,
    input_kind,
    capabilities,
    rejection,
    creator,
    created_at,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
