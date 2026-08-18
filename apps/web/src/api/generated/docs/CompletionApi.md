# CompletionApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**completeDocument**](#completedocument) | **POST** /api/v1/completion | Complete Document|
|[**downloadApprovalExport**](#downloadapprovalexport) | **GET** /api/v1/completion/documents/{document_id}/export | Download Approval Export|
|[**evaluateDocumentCompletion**](#evaluatedocumentcompletion) | **POST** /api/v1/completion/evaluate | Evaluate Completion|

# **completeDocument**
> DocumentCompletionResponse completeDocument(completionRequest)


### Example

```typescript
import {
    CompletionApi,
    Configuration,
    CompletionRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new CompletionApi(configuration);

let completionRequest: CompletionRequest; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.completeDocument(
    completionRequest,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **completionRequest** | **CompletionRequest**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentCompletionResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**201** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **downloadApprovalExport**
> any downloadApprovalExport()


### Example

```typescript
import {
    CompletionApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new CompletionApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.downloadApprovalExport(
    documentId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**any**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**503** | Service Unavailable |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **evaluateDocumentCompletion**
> CompletionEvaluation evaluateDocumentCompletion(completionRequest)


### Example

```typescript
import {
    CompletionApi,
    Configuration,
    CompletionRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new CompletionApi(configuration);

let completionRequest: CompletionRequest; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.evaluateDocumentCompletion(
    completionRequest,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **completionRequest** | **CompletionRequest**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**CompletionEvaluation**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
