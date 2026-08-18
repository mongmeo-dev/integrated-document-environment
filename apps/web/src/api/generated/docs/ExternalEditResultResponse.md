# ExternalEditResultResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **string** |  | [default to undefined]
**document_id** | **string** |  | [default to undefined]
**document_version_id** | **string** |  | [default to undefined]
**original_format** | [**OriginalFormat**](OriginalFormat.md) |  | [default to undefined]
**original_filename** | **string** |  | [default to undefined]
**media_type** | **string** |  | [default to undefined]
**size_bytes** | **number** |  | [default to undefined]
**sha256** | **string** |  | [default to undefined]
**object_key** | **string** |  | [default to undefined]
**status** | [**ExternalEditResultStatus**](ExternalEditResultStatus.md) |  | [default to undefined]
**created_by_id** | **string** |  | [default to undefined]
**created_at** | **string** |  | [default to undefined]
**format_check** | [**FormatCheckResponse**](FormatCheckResponse.md) |  | [default to undefined]

## Example

```typescript
import { ExternalEditResultResponse } from './api';

const instance: ExternalEditResultResponse = {
    id,
    document_id,
    document_version_id,
    original_format,
    original_filename,
    media_type,
    size_bytes,
    sha256,
    object_key,
    status,
    created_by_id,
    created_at,
    format_check,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
