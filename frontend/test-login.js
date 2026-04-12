import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8080/api';

async function testApiCalls() {
    console.log('=== API ENDPOINTS TEST ===\n');

    try {
        // Test health endpoint
        console.log('1. Testing health endpoint...');
        const healthRes = await axios.get(`${API_BASE_URL}/health`);
        console.log('✅ Health:', healthRes.data);

        // Test login
        console.log('\n2. Testing login...');
        const loginRes = await axios.post(`${API_BASE_URL}/auth/login`, {
            username: 'admin',
            password: 'admin123'
        });
        console.log('✅ Login response:', loginRes.data);
        const token = loginRes.data.token;
        console.log('   Token received:', token ? token.substring(0, 20) + '...' : 'none');

        // Test authenticated endpoint
        console.log('\n3. Testing authenticated endpoints...');
        const authHeaders = { Authorization: `Bearer ${token}` };

        // Test get me
        const meRes = await axios.get(`${API_BASE_URL}/auth/me`, { headers: authHeaders });
        console.log('✅ Get me:', meRes.data);

        // Test stats
        const statsRes = await axios.get(`${API_BASE_URL}/stats`, { headers: authHeaders });
        console.log('✅ Stats:', statsRes.data);

        // Test projects
        const projectsRes = await axios.get(`${API_BASE_URL}/projects`, { headers: authHeaders });
        console.log('✅ Projects count:', projectsRes.data?.length || 0);

        // Test reports
        const reportsRes = await axios.get(`${API_BASE_URL}/reports`, { headers: authHeaders });
        console.log('✅ Reports count:', reportsRes.data?.length || 0);

        console.log('\n=== ALL TESTS PASSED ===');
        return true;

    } catch (error) {
        console.error('\n❌ Error:', error.response?.status, error.response?.statusText);
        if (error.response?.data) {
            console.error('Response:', JSON.stringify(error.response.data, null, 2));
        }
        console.error('Stack:', error.stack);
        return false;
    }
}

testApiCalls();
