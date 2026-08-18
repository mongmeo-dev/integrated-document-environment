# DocumentsApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**getDocument**](#getdocument) | **GET** /api/v1/documents/{document_id} | Get Document|
|[**listDocuments**](#listdocuments) | **GET** /api/v1/documents | List Documents|
|[**registerDocument**](#registerdocument) | **POST** /api/v1/documents | Register Document|
|[**validateDocument**](#validatedocument) | **POST** /api/v1/documents/{document_id}/validate | Validate Document|

# **getDocument**
> DocumentResponse getDocument()


### Example

```typescript
import {
    DocumentsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DocumentsApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getDocument(
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

**DocumentResponse**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listDocuments**
> Array<DocumentResponse> listDocuments()


### Example

```typescript
import {
    DocumentsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DocumentsApi(configuration);

let status: DocumentStatus; // (optional) (default to undefined)
let query: string; // (optional) (default to undefined)
let limit: number; // (optional) (default to 20)
let offset: number; // (optional) (default to 0)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listDocuments(
    status,
    query,
    limit,
    offset,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **status** | **DocumentStatus** |  | (optional) defaults to undefined|
| **query** | [**string**] |  | (optional) defaults to undefined|
| **limit** | [**number**] |  | (optional) defaults to 20|
| **offset** | [**number**] |  | (optional) defaults to 0|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**Array<DocumentResponse>**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **registerDocument**
> DocumentResponse registerDocument()


### Example

```typescript
import {
    DocumentsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DocumentsApi(configuration);

let file: File; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.registerDocument(
    file,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **file** | [**File**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**202** | Successful Response |  -  |
|**400** | Bad Request |  -  |
|**401** | Unauthorized |  -  |
|**413** | Content Too Large |  -  |
|**415** | Unsupported Media Type |  -  |
|**503** | Service Unavailable |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **validateDocument**
> DocumentResponse validateDocument()


### Example

```typescript
import {
    DocumentsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DocumentsApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.validateDocument(
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

**DocumentResponse**

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
|**503** | Service Unavailable |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
