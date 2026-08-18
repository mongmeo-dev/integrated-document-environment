# HistoryApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**listHistoryEvents**](#listhistoryevents) | **GET** /api/v1/history | List History Events|

# **listHistoryEvents**
> Array<HistoryEvent> listHistoryEvents()


### Example

```typescript
import {
    HistoryApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new HistoryApi(configuration);

let documentId: string; // (optional) (default to undefined)
let filter: string; // (optional) (default to undefined)
let limit: number; // (optional) (default to 50)
let offset: number; // (optional) (default to 0)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listHistoryEvents(
    documentId,
    filter,
    limit,
    offset,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentId** | [**string**] |  | (optional) defaults to undefined|
| **filter** | [**string**] |  | (optional) defaults to undefined|
| **limit** | [**number**] |  | (optional) defaults to 50|
| **offset** | [**number**] |  | (optional) defaults to 0|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**Array<HistoryEvent>**

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
